void handle_error (int retval);

int exec(int retval);

void initialize();

void available_event_codes(int* res, int* number);

void load_event_names(char* file_path, int* res, int* number);

// the file can be safely removed after next proc.sh execution