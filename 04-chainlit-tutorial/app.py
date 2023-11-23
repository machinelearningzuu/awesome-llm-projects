from configure_models import *

@cl.on_chat_start
def main():
    cl.user_session.set("llm_chain", llm_chain)


@cl.on_message
async def main(message: str):
    llm_chain = cl.user_session.get("llm_chain")  # type: LLMChain
    res = await llm_chain.acall(message.content, callbacks=[cl.AsyncLangchainCallbackHandler()])
    print(res)
    await cl.Message(content=res["text"]).send()