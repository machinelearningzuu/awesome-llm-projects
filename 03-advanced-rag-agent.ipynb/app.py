from configure_models import *

@cl.on_chat_start
async def init():
    files = None
    while files is None:
        files = await cl.AskFileMessage(
                                    content="Please upload a PDF file to begin!",
                                    accept=["application/pdf"],
                                    ).send()

    file = files[0]
    msg = cl.Message(content=f"Processing `{file.name}`…")
    await msg.send()

    pdf_stream = BytesIO(file.content)
    pdf = PyPDF2.PdfReader(pdf_stream)
    pdf_text = ""
    for page in pdf.pages:
        pdf_text += page.extract_text()
        # Split the text into chunks
        texts = text_splitter.split_text(pdf_text)
    # Create metadata for each chunk
    metadatas = [{"source": f"{i}-pl"} for i in range(len(texts))]

    bm25_retriever = BM25Retriever.from_texts(texts)
    bm25_retriever.k=5

    cl.user_session.set("embeddings", bge_embeddings)

    docsearch = await cl.make_async(Qdrant.from_texts)(
                                                        texts, 
                                                        bge_embeddings,
                                                        location=":memory:", 
                                                        metadatas=metadatas
                                                        )

    #Hybrid Search
    qdrant_retriever = docsearch.as_retriever(search_kwargs={"k":5})
    ensemble_retriever = EnsembleRetriever(
                                            retrievers=[bm25_retriever,qdrant_retriever],
                                            weights=[0.5,0.5]
                                            )

    compression_retriever = ContextualCompressionRetriever(
                                                        base_compressor=compressor,
                                                        base_retriever=ensemble_retriever,
                                                        )
    # Create a chain that uses the Chroma vector store
    chain = RetrievalQA.from_chain_type(
                                        llm = llm,
                                        chain_type="stuff",
                                        retriever=compression_retriever,
                                        return_source_documents=True,
                                        # chain_type_kwargs=chain_type_kwargs
                                        )

    # Save the metadata and texts in the user session
    cl.user_session.set("metadatas", metadatas)
    cl.user_session.set("texts", texts)
    
    # Let the user know that the system is ready
    msg.content = f"`{file.name}` processed. You can now ask questions!"
    await msg.update()
    #store the chain as long as the user session is active
    cl.user_session.set("chain", chain)

cl.on_message
async def process_response(res):
    # retrieve the retrieval chain initialized for the current session
    chain = cl.user_session.get("chain") 
    # Chinlit callback handler
    cb = cl.AsyncLangchainCallbackHandler(
                                        stream_final_answer=True, 
                                        answer_prefix_tokens=["FINAL", "ANSWER"]
                                        )
    cb.answer_reached = True
    print("in retrieval QA")
    res = await chain.acall(res, callbacks=[cb])
    print(f"response: {res}")
    answer = res["result"]
    sources = res["source_documents"]
    source_elements = []

    # Get the metadata and texts from the user session
    metadatas = cl.user_session.get("metadatas")
    all_sources = [m["source"] for m in metadatas]
    texts = cl.user_session.get("texts")

    if sources:
        found_sources = []

        # Add the sources to the message
        for source in sources:
            print(source.metadata)
            try :
                source_name = source.metadata["source"]
            except :
                source_name = ""
            # Get the index of the source
            text = source.page_content
            found_sources.append(source_name)
            # Create the text element referenced in the message
            source_elements.append(cl.Text(content=text, name=source_name))

        if found_sources:
            answer += f"\nSources: {', '.join(found_sources)}"
        else:
            answer += "\nNo sources found"

    if cb.has_streamed_final_answer:
        cb.final_stream.elements = source_elements
        await cb.final_stream.update()
    else:
        await cl.Message(content=answer, elements=source_elements).send()


# chainlit run app.py