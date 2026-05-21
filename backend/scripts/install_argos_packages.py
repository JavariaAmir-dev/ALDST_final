import argparse

from argostranslate import package


SUPPORTED_PACKAGES = {
    "ur": ("en", "ur"),
    "arabic": ("en", "ar"),
    "ar": ("en", "ar"),
    "french": ("en", "fr"),
    "fr": ("en", "fr"),
    "spanish": ("en", "es"),
    "es": ("en", "es"),
    "german": ("en", "de"),
    "de": ("en", "de"),
    "urdu": ("en", "ur"),
}


def install_package(from_code: str, to_code: str) -> None:
    package.update_package_index()
    available_packages = package.get_available_packages()
    selected_package = next(
        (
            candidate
            for candidate in available_packages
            if candidate.from_code == from_code and candidate.to_code == to_code
        ),
        None,
    )
    if not selected_package:
        raise SystemExit(f"No Argos package found for {from_code} -> {to_code}.")

    package_path = selected_package.download()
    package.install_from_path(package_path)
    print(f"Installed Argos package: {from_code} -> {to_code}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Install Argos Translate packages for ALDST.")
    parser.add_argument(
        "languages",
        nargs="+",
        help="Target languages/codes to install: urdu, arabic, french, spanish, german, or all",
    )
    args = parser.parse_args()

    selected = list(SUPPORTED_PACKAGES) if "all" in {language.lower() for language in args.languages} else args.languages
    installed_pairs = set()
    for language in selected:
        pair = SUPPORTED_PACKAGES.get(language.lower())
        if not pair:
            raise SystemExit(f"Unsupported target language: {language}")
        if pair in installed_pairs:
            continue
        install_package(*pair)
        installed_pairs.add(pair)


if __name__ == "__main__":
    main()
