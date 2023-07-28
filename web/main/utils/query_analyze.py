from timeit import default_timer as timer
from django.db import connection, reset_queries


def django_query_analyze(func):
    """decorator to perform analysis on Django queries"""

    def wrapper(*args, **kwargs):

        avs = []
        query_counts = []
        queries = []
        for _ in range(50):
            reset_queries()
            start = timer()
            func(*args, **kwargs)
            end = timer()
            avs.append(end - start)
            query_counts.append(len(connection.queries))
            queries = connection.queries
            reset_queries()

        print()
        print(f"ran function {func.__name__}")
        print(f"-" * 20)
        for i, query in enumerate(queries):
            print(f"Query {i+1}\n{query['sql']}")
        print(f"number of queries: {int(sum(query_counts) / len(query_counts))}")
        print(f"Time of execution: {float(format(min(avs), '.5f'))}s")
        print()
        return func(*args, **kwargs)

    return wrapper
