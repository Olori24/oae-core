from oae.agent.loop import AgentLoop


def main():

    print("=" * 40)
    print("      OAE CORE v0.1 ALPHA")
    print("=" * 40)

    loop = AgentLoop()

    result = loop.run(
        "Create a README for this repository."
    )

    print("\nProvider Response:\n")
    print(result)


if __name__ == "__main__":
    main()
