class UsageError(RuntimeError):
    '''
    An error that signals that the user invoked a CLI script with invalid or contradictory arguments.

    The application should close gracefully with a nonzero error code.

    The 'message' of this error is guaranteed to be clear as to what went wrong and what to do to resolve the issue. (Therefore, printing a stacktrace is not necessary)
    '''
    pass

