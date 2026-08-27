QNN_SDK_ROOT ?= /home/devuser/qairt/2.47.0.260601
CXX          ?= g++

QNN_INCLUDE  := $(QNN_SDK_ROOT)/include/QNN
QNN_LIB_DIR  := $(QNN_SDK_ROOT)/lib/aarch64-ubuntu-gcc9.4

CXXFLAGS := -std=gnu++11 -Wall -Werror -fPIC -O2 \
            -Wno-write-strings -Wno-unused-variable \
            -I. -I$(QNN_INCLUDE)

LDFLAGS  := -L$(QNN_LIB_DIR) -Wl,-rpath,$(QNN_LIB_DIR) -ldl -lpthread

SRCS := main.cpp qnn_inference.cpp ipc_handler.cpp
OBJS := $(SRCS:.cpp=.o)
TARGET := kawach_worker

.PHONY: all clean
all: $(TARGET)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $(OBJS) $(LDFLAGS)
	@echo "Built: $(TARGET)"

clean:
	rm -f $(OBJS) QnnWrapperUtils.o $(TARGET)
