from app.agent.planner import run_planned_analysis
from app.gee import initialize_gee
from app.config import GEE_PROJECT_ID

def main():
    initialize_gee(GEE_PROJECT_ID)

    prompt = """
Assess the vegetation and land-cover characteristics
of this area for 2025.

I want both vegetation information and land-cover
composition for the same period.
"""

    shared_arguments = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [76.80, 28.35],
                    [77.20, 28.35],
                    [77.20, 28.65],
                    [76.80, 28.65],
                    [76.80, 28.35],
                ]
            ],
        },
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
    }

    print("1. Running planned analysis...")

    result = run_planned_analysis(
        prompt,
        shared_arguments,
    )

    print("\n2. PLAN")
    print(result["plan"])

    print("\n3. ANALYSIS RESULTS")

    for item in result["results"]:
        print(f"\nTool: {item['tool']}")
        print(f"Reason: {item['reason']}")
        print(f"Result: {item['result']}")
        print(f"Validation: {item['validation']}")

    print("\n4. FINAL SYNTHESIZED ANSWER")
    print(result["answer"])


if __name__ == "__main__":
    main()
