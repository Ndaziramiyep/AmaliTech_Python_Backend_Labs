def list_authors(authors):
    """Display all authors with their nationality and birth year."""
    if not authors:
        print("No authors found.")
        return
    print("\nAuthors:")
    for a in authors:
        print(f"{a.name} | Nationality: {a.nationality or 'N/A'} | Birth year: {a.birth_year or 'N/A'}")
