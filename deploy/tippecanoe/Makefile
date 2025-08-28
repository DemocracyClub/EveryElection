.PHONY: all clean build_in_src_dir

TIPPECANOE_VERSION = 2.79.0
TARBALL = tippecanoe-$(TIPPECANOE_VERSION).tar.gz
SRC_DIR = tippecanoe-$(TIPPECANOE_VERSION)
INSTALL_DIR = /usr/local

all: $(INSTALL_DIR)/bin/tippecanoe

build_in_src_dir: $(INSTALL_DIR)/$(SRC_DIR)/tippecanoe

$(INSTALL_DIR)/$(TARBALL):
	wget https://github.com/felt/tippecanoe/archive/refs/tags/$(TIPPECANOE_VERSION).tar.gz -O $@

$(INSTALL_DIR)/$(SRC_DIR)/Makefile: $(INSTALL_DIR)/$(TARBALL)
	tar --touch -xvzf  $< -C $(INSTALL_DIR)

$(INSTALL_DIR)/$(SRC_DIR)/tippecanoe: $(INSTALL_DIR)/$(SRC_DIR)/Makefile
	cd $(dir $<) && make

$(INSTALL_DIR)/bin/tippecanoe: $(INSTALL_DIR)/$(SRC_DIR)/tippecanoe
	cd $(dir $<) && sudo make install PREFIX=$(INSTALL_DIR)

clean:
	rm -rf $(INSTALL_DIR)/$(SRC_DIR) $(INSTALL_DIR)/$(TARBALL)