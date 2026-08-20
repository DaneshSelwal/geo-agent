from app.agent.llm import create_gemini_client


def main():
    client = create_gemini_client()

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Say hello in one sentence.",
    )

    print(response.text)


if __name__ == "__main__":
    main()
