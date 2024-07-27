import importlib.resources as resources


def import_string_resource(package, resource):
    return resources.files(package).joinpath(resource).read_text()
