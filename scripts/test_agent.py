# scripts/test_agent.py

from app.agent.agent import run_agent
from app.gee import initialize_gee
from app.config import GEE_PROJECT_ID


def main():
    initialize_gee(GEE_PROJECT_ID)

    prompt = """
            You are a geospatial analysis assistant.

            The user wants to understand the land-cover composition
            of the specified area.

            Use the most appropriate available tool.

            The area of interest is:

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

            Analyze land cover from 2025-01-01
            to 2025-12-31.
            """

    answer = run_agent(prompt)

    print("\nFINAL ANSWER")
    print(answer)


if __name__ == "__main__":
    main()
