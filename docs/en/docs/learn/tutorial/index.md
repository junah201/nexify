# Tutorial

This tutorial shows you how to use **Nexify** with most of its features, step by step.

Each section gradually builds on the previous ones, but it's structured to separate topics, so that you can go directly to any specific one to solve your specific API needs.

# Run the Code in Tutorial

All the code blocks can be copied and used directly (they are actually tested Python files).

It is highly encouraged that you write or copy the code, edit it and run it locally.

Using it in your editor is what really shows you the benefits of **Nexify**, seeing how little code you have to write, all the type checks, autocompletion, etc.

---

# Install Nexify

The first step is to install **Nexify**.

Make sure you create a virtual environment, activate it, and than **install Nexify**.

In the tutorial, we recommend installing all optional dependencies together.

<div class="termy">

```console
$ pip install "nexify[cli]"

---> 100%
```

</div>

/// info
Make sure you put "nexify[cli]" in quotes to ensure it works in all terminals.
///


/// info
`nexify[cli]` includes several dependencies required for the development environment.
If you're deploying Nexify to production, you can install it like this:

```py
pip install nexify
```
///
