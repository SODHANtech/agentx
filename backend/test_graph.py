from langchain_core.messages import HumanMessage

from backend.graph import graph

config = {
    "configurable": {
        "thread_id": "satya"
    }
}

response = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="What is the attendance policy?"
            )
        ]
    },
    config=config
)

print(response["messages"][-1].content)