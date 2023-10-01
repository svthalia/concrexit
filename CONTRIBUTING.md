# Contributing to concrexit

**Make sure to read the [README](README.md) first! It contains a lot of information about the project.**

## How to contribute

### Your first contribution
For people that are new to Django, we have created [the infamous "shoe size" issue](https://github.com/svthalia/concrexit/wiki/your-first-contribution), which is a very simple issue that can be used to get familiar with the code base and the development process, while showing you around through the most essential parts of our website.

### When working on an issue

- Make sure you are not working on the main branch but on a separate branch.
- Assign the issue to yourself on GitHub.
- Make sure not just to read the issue but also the conversation below the issue.

### When opening a pull request

- Make sure to reference the issue you are working on in the pull request.
- Make sure the pull request has a descriptive title and description.
- Make sure to add a screenshot of the changes if they are visual (e.g. CSS changes).
- Make sure the pull request has all the necessary labels. GitHub actions will automatically add some labels, but you might need to add some yourself.
- If your pull request is not ready for review yet, mark it as draft.
- If your pull request does not succeed the tests, make sure to fix the tests. If you want someone to review your code before fixing the tests, explicitly request someone for a review.
- Check your own changes. Sometimes, just looking through the diff yourself already reveals some mistakes before someone else has to point them out.
- Keep an eye on your pull request. Just because you have opened a pull request does not mean you are done. You might get comments or requests for changes, so make sure to check your pull request regularly. If you don't get any comments, you can always ask someone to review your pull request.

### When reviewing a pull request

- Make sure to read the code and understand what it does
- Be friendly and **constructive** in your comments
- Use code suggestions to make small changes
- Ask questions if you don't understand something, rather than making assumptions
- If you have a lot of comments, consider having a conversation with the author in person rather than in the pull request


## About the code

### Documentation
We have tried a lot of ways to document our code.
We have tried to use elaborate docstrings everywhere, but we have found that they are not very useful on most places.
We have also tried to use Sphinx, but we have found that it is too much work to keep the documentation up to date, nor do people actually read it.
We also have used a GitHub wiki, but we have found that it is not very useful either because it is not easy to find and read (and it is not versioned with the code!)

The best way to document our code is of course to write good, well-readable and self-explanatory code.
Additionally, we've found that simple markdown files in the app root are useful, because they are easy to find and read.
The GitHub flavoured markdown is also very useful because it is easy to link to other files, issues, etc. and it can even render graphs!

Our conclusion is thus that we should:

- Write good code that is easy to read and understand, using good names for variables, functions, etc.
- Where necessary, write comments in the code (e.g. when the code is not self-explanatory). Try to place comments on a place a future reader (that should read them) would expect them.
- Use type hints and docstrings where useful, but don't overdo it.
- For more elaborate documentation, write markdown files in the app root, explaining the purpose of the app, the high-level architecture, etc.
- Always _explain why_ something is done in a certain way, not just _how_ it is done.
- Have a README.md and CONTRIBUTING.md, explaining how to set up the app, how to run the tests, etc.
- The GitHub wiki can be used for more volatile information, like internal processes, getting started guides, etc.

> Currently, we are still in the process of migrating the documentation to the new format.

### Language
Try to use British English as much as possible.

### Translations
We used to have concrexit available in both Dutch and English, but we have decided to drop the Dutch translation.
This is because we have found that it is a lot of work to keep the translations up to date, and we have found that it is not really necessary to have a Dutch translation.
It is good practice, in our code, to do use the `gettext` functions (often imported as `_`) for all strings that are visible to the user, so that could be easy to add translations in the future.
However, this has not been consistently done, so this is not a priority. We do not have plans to re-introduce translations any time soon.

### Code style
Our code style is based on the [Django coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/).

All code has to be run through [isort](https://github.com/PyCQA/isort) and [`black`](https://github.com/psf/black) before being committed. To isort and black the code before committing run `make fmt` one the base directory of this project. We also use [pre-commit](https://pre-commit.com) to make sure you don't forget about this. Pre-commit is automatically installed by `make`.
If you want to integrate `black` with your editor look in the [`black` docs](https://black.readthedocs.io/en/stable/editor_integration.html). On linux you can find the black executable in `~/.cache/poety/virtualenvs/<your env>/bin/black`.

### Tests
Writing tests is good practice, but we will admit, it is also boring, we don't do it enough, and we are not very good at it.
We require 100% test coverage for certain, critical modules.
Apart from that, we don't have any strict rules about test coverage, but we do encourage you to write tests for your code.
Most of our tests are unit tests. We also have some integration tests, but not enough (we definitely need more of those).

You can run all the tests with `make test`, afterwards you can check the coverage with `make coverage`.
