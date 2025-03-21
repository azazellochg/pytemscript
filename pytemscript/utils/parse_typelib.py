#!/usr/bin/env python3
import comtypes.client

from pytemscript.utils.constants import *

EXCLUDED_METHODS = [
    "QueryInterface",
    "AddRef",
    "Release",
    "GetTypeInfo",
    "GetTypeInfoCount",
    "GetIDsOfNames",
    "Invoke",
    "Item",
    "_NewEnum",
    "Count"
]


def list_typelib_details(prog_id: str):
    """ Parse COM interface methods and enumerations. """
    try:
        com_obj = comtypes.client.CreateObject(prog_id)
        print("OK")
    except:
        print("FAIL")
        return None, None, None

    constants = comtypes.client.Constants(com_obj)
    typeinfo = com_obj.GetTypeInfo(0)
    typelib = typeinfo.GetContainingTypeLib()[0]
    lib_attr = typelib.GetLibAttr()
    typelib_version = "%d.%d" % (lib_attr.wMajorVerNum, lib_attr.wMinorVerNum)

    enums = constants.enums
    interfaces = {}

    # Iterate through TypeInfo elements in the Type Library
    for i in range(typelib.GetTypeInfoCount()):
        typeinfo = typelib.GetTypeInfo(i)
        typeattr = typeinfo.GetTypeAttr()

        # Extract Dispatch
        if typeattr.typekind == 4:
            interface_name = typeinfo.GetDocumentation(-1)[0]
            # interface_desc = typeinfo.GetDocumentation(-1)[1]
            methods = []

            # Extract method names from the interface
            for j in range(typeattr.cFuncs):
                func_desc = typeinfo.GetFuncDesc(j)
                method_name = typeinfo.GetNames(func_desc.memid)[0]
                if method_name not in EXCLUDED_METHODS and method_name not in methods:
                    methods.append(method_name)

            interfaces[interface_name] = methods

    return enums, interfaces, typelib_version


def create_output():
    """ Save output into txt. """
    for prog_id in [
        SCRIPTING_STD,
        SCRIPTING_ADV,
        SCRIPTING_LOWDOSE,
        SCRIPTING_TIA,
        SCRIPTING_TECNAI_CCD2,
        SCRIPTING_TECNAI_CCD
    ]:
        print("Querying %s..." % prog_id, end="")
        enums, interfaces, version = list_typelib_details(prog_id)
        if enums is not None:
            with open("%s_version%s.txt" % (prog_id, version), "w") as f:
                f.write("========== Enumerations =========\n")
                for enum, values in enums.items():
                    f.write("- %s\n" % enum)
                    for name, value in values.items():
                        f.write("\t%s = %s\n" % (name, value))

                f.write("\n========== Interfaces ===========\n")
                for interface, methods in interfaces.items():
                    f.write("- %s\n" % interface)
                    for method in methods:
                        f.write("\t%s\n" % method)


if __name__ == '__main__':
    create_output()
