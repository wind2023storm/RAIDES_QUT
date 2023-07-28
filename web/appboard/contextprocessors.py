from project.forms import CreateProjectForm


def create_project_form(request):
    """Used to pass the Create Project Form to every page that inherits the base template"""
    return {'createProjectForm': CreateProjectForm()}
