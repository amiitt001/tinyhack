import os

from tinyfish import TinyFish
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    if not os.getenv("TINYFISH_API_KEY"):
        raise SystemExit(
            "TINYFISH_API_KEY is not set. Add your TinyFish API key to the "
            "run configuration environment, or run:\n"
            "  export TINYFISH_API_KEY='your-api-key'"
        )

    os.environ["TINYFISH_RUNTIME_ATTEMPT_ID"] = (
        "7a9d8070-75d8-490e-8916-50a687b7dac2"
    )
    client = TinyFish()

    response = client.search.query(
        "latest FIFA World Cup news today",
        location="US",
        language="en",
    )

    for result in response.results:
        print(result.title, result.url)


if __name__ == "__main__":
    main()