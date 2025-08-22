.PHONY: all clean

TIPPECANOE_VERSION = 2.79.0
TIPPECANOE_TARBALL = tippecanoe-$(TIPPECANOE_VERSION).tar.gz
TIPPECANOE_SRC_DIR = tippecanoe-$(TIPPECANOE_VERSION)
INSTALL_DIR = /usr/local

all: tippecanoe clean

$(TIPPECANOE_TARBALL):
	wget https://github.com/felt/tippecanoe/archive/refs/tags/$(TIPPECANOE_VERSION).tar.gz -O $(TIPPECANOE_TARBALL)

$(TIPPECANOE_SRC_DIR): $(TIPPECANOE_TARBALL)
	tar -xvzf $(TIPPECANOE_TARBALL)

tippecanoe: $(TIPPECANOE_SRC_DIR)
	@if command -v $(INSTALL_DIR)/bin/tippecanoe >/dev/null 2>&1; then \
		echo "tippecanoe already installed at $(INSTALL_DIR)/bin/tippecanoe, skipping build."; \
	else \
		cd $(TIPPECANOE_SRC_DIR) && make && sudo make install PREFIX=$(INSTALL_DIR); \
	fi

clean:
	rm -rf $(TIPPECANOE_SRC_DIR) $(TIPPECANOE_TARBALL)