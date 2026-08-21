# dap.gal's website project

![dap.gal](https://img.shields.io/badge/dap.gal-Project-00C853?style=for-the-badge)

Personal and professional website of **David Álvarez**, focused on **system administration, cybersecurity, virtualization, and Linux infrastructure**.

🌐 **Website:** [dap.gal](https://dap.gal/)

---

## About

This repository contains the source code for [dap.gal](https://dap.gal/), a technical website built with **MkDocs** and **Material for MkDocs**.

The site is used to publish:

* 📝 Technical articles and blog posts.
* 🐧 Linux guides and documentation.
* 🧰 Cheatsheets and quick references.
* 💻 Projects and infrastructure-related resources.
* 📬 Contact information.

The website is generated as a static site from Markdown files, making the content easy to maintain, version, and deploy.

---

## Technologies

The project is primarily built with:

* [MkDocs](https://www.mkdocs.org/) — Static site generator based on Markdown.
* [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) — Documentation theme and framework.
* [MkDocs Blog Plugin](https://github.com/mkdocs-material/mkdocs-material) — Blog functionality.
* [MkDocs RSS Plugin](https://github.com/Guts/mkdocs-rss-plugin) — RSS feed generation.
* [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) — Extended Markdown functionality.
* [Pillow](https://python-pillow.org/) — Image processing.

Python dependencies are defined in [`requirements.txt`](./requirements.txt).

---

## Project Structure

```text
.
├── .github/
│   └── workflows/       # GitHub Actions workflows
├── projects/             # Subprojects
├── root/                 # Main project
│   ├── assets/           # Images, stylesheets and other assets
│   └── ...
├── .gitignore
├── git                  # Git-related configuration/resources
├── mkdocs.yml            # MkDocs configuration
├── requirements.txt      # Python dependencies
└── README.md
```

Most of the website content lives inside the `root/` directory, which is configured as the MkDocs documentation directory.

---

## Local Development

### Requirements

Make sure you have the following installed:

* Python 3
* `pip`
* Git

### 1. Clone the repository

```bash
git clone https://github.com/dap-gal/web.git
cd web
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the development server

```bash
mkdocs serve
```

The website will normally be available at:

```text
http://127.0.0.1:8000/
```

MkDocs automatically reloads the site whenever the source files are modified.

---

## Build the Website

To generate the static website:

```bash
mkdocs build
```

The generated files will be placed in:

```text
site/
```

For a stricter build that also validates the configuration and warnings:

```bash
mkdocs build --strict
```

---

## Website Sections

The main navigation is organized into the following sections:

| Section         | Description                      |
| --------------- | -------------------------------- |
| 🏠 Home         | Main landing page                |
| 📝 Blog         | Technical articles and posts     |
| 🐧 Linux Manual | Linux documentation and commands |
| 🧰 Cheatsheet   | Quick technical references       |
| 📬 Contact      | Contact information              |

The navigation structure is defined in `mkdocs.yml`.

---

## Adding Content

Website content is primarily written in **Markdown**.

To add or modify a page:

1. Create or edit the appropriate `.md` file inside `root/`.
2. Write the content using Markdown.
3. Preview the changes with `mkdocs serve`.
4. Commit your changes.
5. Push them to the repository and let the configured deployment workflow publish them.

### Example

````markdown
# My New Article

A short introduction to the article.

## Introduction

Article content goes here.

## Commands

(```bash
sudo systemctl status nginx
```)
````

---

## 🎨 Customization

The main visual and functional configuration is defined in `mkdocs.yml`.

The website currently uses:

- **Material for MkDocs** as the theme.
- Spanish as the interface language.
- `slate` as the default theme.
- Black as the primary color.
- Green as the accent color.
- **JetBrains Mono** as the main font.
- Instant navigation.
- Advanced search.
- Code block copying.
- Top navigation.
- Tabs and collapsible content.
- Custom CSS.

Additional styling is loaded from:

```text
root/assets/css/extra.css
````

---

## Deployment

The website is available at:

**https://dap.gal/**

The project's MkDocs configuration defines `https://dap.gal/` as the canonical site URL.

The repository also contains **GitHub Actions** workflows for project automation and deployment.

---

## Contributing

This is primarily a personal project, but suggestions, corrections, and improvements are welcome.

If you find:

* A technical issue.
* A broken link.
* A spelling mistake.
* Outdated information.
* A documentation improvement.

feel free to open an **Issue** or submit a **Pull Request**.

---

## Contact

You can find the available contact channels and social networks at:

- **[dap.gal](https://dap.gal/)**
- **[t.me/sudodap](https://t.me/sudodap/)**

The website currently links to platforms including:

* X / Twitter
* YouTube
* Twitch
* Telegram
* Instagram
* Discord

---

## License

Please refer to the license files and notices included in the repository for the applicable terms regarding the use and distribution of the project's content.

---

<p align="center">
  <strong><a href="https://dap.gal" target="_blank" style="color:white">dap.gal</a></strong><br>
 Cybersecurity · Systems Administration · Infrastructure
</p>
