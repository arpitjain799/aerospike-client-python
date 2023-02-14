/*******************************************************************************
 * Copyright 2013-2021 Aerospike, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

#pragma once

// convert python 2.x calls to python 3.x
#if PY_MAJOR_VERSION >= 3
    #if PY_MINOR_VERSION < 7
        #define PyString_AsString PyUnicode_AsUTF8
    #else
        #define PyString_AsString (char *)PyUnicode_AsUTF8
        #define PyEval_InitThreads Py_Initialize
    #endif
#endif

// define module definition and initialization macros
#if PY_MAJOR_VERSION >= 3
    #define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
    #define MOD_DEF(ob, name, doc, size, methods, clear)                       \
        static struct PyModuleDef moduledef = {PyModuleDef_HEAD_INIT,          \
                                               name,                           \
                                               doc,                            \
                                               size,                           \
                                               methods,                        \
                                               NULL,                           \
                                               NULL,                           \
                                               clear};                         \
        ob = PyModule_Create(&moduledef);
    #define MOD_SUCCESS_VAL(val) val
#else
    #define MOD_INIT(name) PyMODINIT_FUNC init##name(void)
    #define MOD_DEF(ob, name, doc, size, methods, clear)                       \
        ob = Py_InitModule3(name, methods, doc);
    #define MOD_SUCCESS_VAL(val)
#endif

// pyval is a PyObject* classname is a string
#define AS_Matches_Classname(pyval, classname)                                 \
    (strcmp((pyval)->ob_type->tp_name, (classname)) == 0)
