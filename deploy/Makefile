.PHONY: all clean

TIPPECANOE_VERSION = 2.79.0
TARBALL = tippecanoe-$(TIPPECANOE_VERSION).tar.gz
SRC_DIR = tippecanoe-$(TIPPECANOE_VERSION)
INSTALL_DIR = /usr/local

all: $(INSTALL_DIR)/bin/tippecanoe

$(INSTALL_DIR)/$(TARBALL):
	wget https://github.com/felt/tippecanoe/archive/refs/tags/$(TIPPECANOE_VERSION).tar.gz -O $@

$(INSTALL_DIR)/$(SRC_DIR): $(INSTALL_DIR)/$(TARBALL)
	tar --touch -xvzf  $< -C $(INSTALL_DIR)

$(INSTALL_DIR)/bin/tippecanoe: $(INSTALL_DIR)/$(SRC_DIR)
	cd $< && make && sudo make install PREFIX=$(INSTALL_DIR)
	sudo touch $@

clean:
	rm -rf $(INSTALL_DIR)/$(SRC_DIR) $(INSTALL_DIR)/$(TARBALL)