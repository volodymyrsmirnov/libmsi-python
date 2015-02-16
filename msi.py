from cffi import FFI

ffi = FFI()

ffi.cdef("""
   typedef struct _GError GError;

    struct _GError
    {
      unsigned int domain;
      int code;
      char *message;
    };

    typedef struct _GArray GArray;

    struct _GArray {
        char *data;
        unsigned int len;
    };

    void g_type_init();
    void g_object_unref(void *pointer);
    void g_clear_error (GError **err);

    typedef struct _LibmsiDatabase LibmsiDatabase;
    typedef struct _LibmsiQuery LibmsiQuery;
    typedef struct _LibmsiRecord LibmsiRecord;
    typedef struct _LibmsiSummaryInfo LibmsiSummaryInfo;

    LibmsiDatabase * libmsi_database_new (const char *path, unsigned int flags, const char *persist, GError **error);
    LibmsiSummaryInfo * libmsi_summary_info_new (LibmsiDatabase *database, unsigned update_count, GError **error);
    int libmsi_summary_info_get_property_type (LibmsiSummaryInfo *si, int prop, GError **error);
    int libmsi_summary_info_get_int (LibmsiSummaryInfo *si, int prop, GError **error);
    const char * libmsi_summary_info_get_string (LibmsiSummaryInfo *si, int prop, GError **error);
    long libmsi_summary_info_get_filetime (LibmsiSummaryInfo *si, int prop, GError **error);
    LibmsiQuery * libmsi_query_new (LibmsiDatabase *database, const char *query, GError **error);
    int libmsi_query_execute (LibmsiQuery *query, LibmsiRecord *rec, GError **error);
    LibmsiRecord * libmsi_query_get_column_info (LibmsiQuery *query, int info, GError **error);
    unsigned int libmsi_record_get_field_count (const LibmsiRecord *record);
    int libmsi_record_is_null (const LibmsiRecord *record, unsigned int field);
    char * libmsi_record_get_string (const LibmsiRecord *record, unsigned int field);
    LibmsiRecord * libmsi_query_fetch (LibmsiQuery *query, GError **error);
    int libmsi_query_close (LibmsiQuery *query, GError **error);
""")

libmsi = ffi.dlopen("libmsi.so")


class MSIException(Exception):
    pass


class MSI(object):
    __error = ffi.new("GError**")
    __database = ffi.NULL

    def __init__(self, path_to_msi, mode=1 << 0, persist=ffi.NULL):
        try:
            libmsi.g_type_init()
        except:
            pass

        if persist != ffi.NULL:
            persist = ffi.new("char[]", persist)

        self.__database = libmsi.libmsi_database_new(
            ffi.new("char[]", path_to_msi), mode, persist, self.__error)

        if self.__database == ffi.NULL or self.__error[0] != ffi.NULL:
            raise MSIException("MSI read error")

    _summary_info = None

    @property
    def summary_info(self):
        if self._summary_info is not None:
            return self._summary_info

        msi_summary = libmsi.libmsi_summary_info_new(self.__database, 0, self.__error)

        if self.__error[0] != ffi.NULL:
            raise MSIException("MSI SummaryInfo read error")

        summary_info_fields = {
            "LIBMSI_PROPERTY_DICTIONARY": 0,
            "LIBMSI_PROPERTY_CODEPAGE": 1,
            "LIBMSI_PROPERTY_TITLE": 2,
            "LIBMSI_PROPERTY_SUBJECT": 3,
            "LIBMSI_PROPERTY_AUTHOR": 4,
            "LIBMSI_PROPERTY_KEYWORDS": 5,
            "LIBMSI_PROPERTY_COMMENTS": 6,
            "LIBMSI_PROPERTY_TEMPLATE": 7,
            "LIBMSI_PROPERTY_LASTAUTHOR": 8,
            "LIBMSI_PROPERTY_UUID": 9,
            "LIBMSI_PROPERTY_EDITTIME": 10,
            "LIBMSI_PROPERTY_LASTPRINTED": 11,
            "LIBMSI_PROPERTY_CREATED_TM": 12,
            "LIBMSI_PROPERTY_LASTSAVED_TM": 13,
            "LIBMSI_PROPERTY_VERSION": 14,
            "LIBMSI_PROPERTY_SOURCE": 15,
            "LIBMSI_PROPERTY_RESTRICT": 16,
            "LIBMSI_PROPERTY_THUMBNAIL": 17,
            "LIBMSI_PROPERTY_APPNAME": 18,
            "LIBMSI_PROPERTY_SECURITY": 19
        }

        if self._summary_info is None:
            self._summary_info = dict()

        for summary_info_key, summary_info_value in summary_info_fields.items():
            summary_property_type = libmsi.libmsi_summary_info_get_property_type(
                msi_summary, summary_info_value, self.__error
            )

            if self.__error[0] != ffi.NULL:
                continue

            if summary_property_type == 0:
                self._summary_info[summary_info_key] = None
            elif summary_property_type == 1:
                self._summary_info[summary_info_key] = libmsi.libmsi_summary_info_get_int(
                    msi_summary, summary_info_value, self.__error
                )
            elif summary_property_type == 2:
                self._summary_info[summary_info_key] = ffi.string(libmsi.libmsi_summary_info_get_string(
                    msi_summary, summary_info_value, self.__error
                ))
            elif summary_property_type == 3:
                self._summary_info[summary_info_key] = libmsi.libmsi_summary_info_get_filetime(
                    msi_summary, summary_info_value, self.__error
                )

        return self._summary_info

    def query(self, sql):
        return MSIQuery(self.__database, sql)

    def __del__(self):
        if self.__database != ffi.NULL:
            libmsi.g_object_unref(self.__database)

        if self.__error != ffi.NULL:
            libmsi.g_clear_error(self.__error)


class MSIQuery(object):
    __error = ffi.new("GError**")
    __database = ffi.NULL
    __sql = ffi.NULL
    __query = ffi.NULL

    results = []

    def parse_record(self, record):
        if record == ffi.NULL:
            return

        record_parsed = []

        for field in range(1, libmsi.libmsi_record_get_field_count(record) + 1):
            if libmsi.libmsi_record_is_null(record, field):
                record_parsed.append(None)
            else:
                value = libmsi.libmsi_record_get_string(record, field)
                record_parsed.append(ffi.string(value))

        return record_parsed

    def __init__(self, database, sql):
        self.__database = database
        self.__sql = sql

        self.__query = libmsi.libmsi_query_new(self.__database, ffi.new("char[]", self.__sql), self.__error)

        if self.__query == ffi.NULL or self.__error[0] != ffi.NULL:
            raise MSIException("Query parsing error in {0}: {1}".format(self.__sql, ffi.string(self.__error[0].message)))

        if not libmsi.libmsi_query_execute(self.__query, ffi.NULL, self.__error):
            raise MSIException("Query execution error in '{0}'".format(self.__sql))

        record_column_names = self.parse_record(libmsi.libmsi_query_get_column_info(self.__query, 0, self.__error))
        record_column_types = self.parse_record(libmsi.libmsi_query_get_column_info(self.__query, 1, self.__error))

        self.results.append(record_column_names)
        self.results.append(record_column_types)

        while True:
            record = libmsi.libmsi_query_fetch(self.__query, self.__error)

            if record == ffi.NULL or self.__error[0] != ffi.NULL:
                break

            self.results.append(self.parse_record(record))

            libmsi.g_object_unref(record)

    def __del__(self):
        if self.__error != ffi.NULL:
            libmsi.g_clear_error(self.__error)

        if self.__query != ffi.NULL:
            libmsi.libmsi_query_close(self.__query, ffi.NULL)