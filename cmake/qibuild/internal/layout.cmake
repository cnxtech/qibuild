## Copyright (C) 2011 Aldebaran Robotics

#warning findmodule.*.sdk.in and sdk.cmake use implicit relative path
#between _SDK_LIB and _SDK_CMAKE_MODULES, name could be change, but
#the relative path between each var should remain the same.

qi_set_global(QI_SDK_BIN            "bin"        )
qi_set_global(QI_SDK_LIB            "lib"        )
qi_set_global(QI_SDK_FRAMEWORK      "Frameworks" )
qi_set_global(QI_SDK_INCLUDE        "include"    )
qi_set_global(QI_SDK_SHARE          "share"      )
qi_set_global(QI_SDK_CONF           "etc"        )
qi_set_global(QI_SDK_DOC            "share/doc"  )
qi_set_global(QI_SDK_CMAKE          "share/cmake")
qi_set_global(QI_SDK_CMAKE_MODULES  "cmake")

mark_as_advanced(QI_SDK_BIN
                 QI_SDK_LIB
                 QI_SDK_INCLUDE
                 QI_SDK_SHARE
                 QI_SDK_CONF
                 QI_SDK_DOC
                 QI_SDK_CMAKE
                 QI_SDK_CMAKE_MODULES)
