from invoke import task

@task
def lock(c):
    c.run("pipenv lock --dev")
    c.run("pipenv lock -r > requirements.txt")
    c.run("pipenv lock --dev -r > requirements.dev.txt")