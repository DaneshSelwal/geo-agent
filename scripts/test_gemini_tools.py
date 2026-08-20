from app.agent.gemini import ask_gemini


def main():
    prompt = """
            You are a geospatial analysis assistant.

            The user wants to know about vegetation.

            Choose the most appropriate available tool.

            The area of interest is this GeoJSON polygon:

            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [76.80, 28.35],
                        [77.20, 28.35],
                        [77.20, 28.65],
                        [76.80, 28.65],
                        [76.80, 28.35]
                    ]
                ]
            }

            Analyze vegetation for the period from 2025-01-01
            to 2025-12-31.
            """

    response = ask_gemini(prompt)

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.function_call:
                print("FUNCTION CALL")
                print("Name:", part.function_call.name)
                print("Arguments:", part.function_call.args)
                return

    print("NO FUNCTION CALL")
    print(response.text)


if __name__ == "__main__":
    main()
