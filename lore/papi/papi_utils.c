void handle_error (int retval) {
    printf("PAPI error %d: %s\n", retval, PAPI_strerror(retval));
    exit(1);
}

int exec(int retval) {
    if (retval != PAPI_OK) handle_error(retval);
    return retval;
}