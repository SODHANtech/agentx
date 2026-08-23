from backend.graph import graph

config = {
    "configurable": {
        "thread_id": "satya"
    }
}

result = graph.invoke(
    {
        "messages": []
    },
    config=config
)

print(result)