import speedtest
import pprint


def run_speedtest_debug():
    """
    Runs a speed test and prints the entire raw results dictionary for debugging.
    """
    print("🚀 Starting speed test... This may take a moment.")

    try:
        st = speedtest.Speedtest()

        print("Finding the best server...")
        st.get_best_server()

        print("Performing download test...")
        st.download()

        print("Performing upload test...")
        st.upload(pre_allocate=False)

        print("\n" + "=" * 50)
        print("✅ Speed test complete!")
        print("Raw Results Dictionary:")
        print("=" * 50)

        # Use pprint for a clean, readable dictionary output
        pprint.pprint(st.results.dict())

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    run_speedtest_debug()
