cmake_minimum_required(VERSION 3.10 FATAL_ERROR)
set(PROJECT_NAME "MarkerTracker")
project(${PROJECT_NAME})

find_package(OpenCV REQUIRED )
INCLUDE_DIRECTORIES( ${OpenCV_INCLUDE_DIRS} )

# force static runtime libraries for msvc builds
if(MSVC)
  set(variables CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE CMAKE_CXX_FLAGS_RELWITHDEBINFO CMAKE_CXX_FLAGS_MINSIZEREL)
  foreach(variable ${variables})
	if(${variable} MATCHES "/MD")
	  string(REGEX REPLACE "/MD" "/MT" ${variable} "${${variable}}")
	endif()
  endforeach()
endif()

# set c++17
set(CMAKE_CXX_STANDARD          17 )
set(CMAKE_CXX_STANDARD_REQUIRED ON ) 
set(CMAKE_CXX_EXTENSIONS        OFF)

# compile everything position independent (even static libraries)
set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

# set lto
include(CheckIPOSupported)
check_ipo_supported(RESULT lto_is_supported OUTPUT output)
if(lto_is_supported)
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()

if(MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
  set(CMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO "${CMAKE_EXE_LINKER_FLAGS_RELWITHDEBINFO} /PROFILE")
else()
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
endif()



set(PROJECT_SOURCES
	src/Blob.cpp
	src/BlobDetector.cpp
	src/BlobTracker.cpp
	src/CaptureYUV.cpp
	src/FileManager.cpp
  src/main.cpp)

set(PROJECT_HEADERS
	src/Blob.h
	src/BlobDetector.h
	src/BlobTracker.h
	src/CaptureYUV.h
	src/FileManager.h
	src/utils.h)
				 						 	 
source_group("Source Files" FILES ${PROJECT_SOURCES})
source_group("Header Files" FILES ${PROJECT_HEADERS})

add_executable(${PROJECT_NAME} ${PROJECT_SOURCES} ${PROJECT_HEADERS})
target_link_libraries(${PROJECT_NAME} ${OpenCV_LIBS})