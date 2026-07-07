def list_authors(authors):
    print("\nAuthors:")
    for a in authors:
        print(f"{a.name} | Nationality: {a.nationality or 'N/A'} | Birth year: {a.birth_year or 'N/A'}")
