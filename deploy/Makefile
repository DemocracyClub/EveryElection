.PHONY: all clean tippecanoe_install

TIPPECANOE_VERSION = 2.79.0
TIPPECANOE_TARBALL = tippecanoe-$(TIPPECANOE_VERSION).tar.gz
TIPPECANOE_SRC_DIR = tippecanoe-$(TIPPECANOE_VERSION)
INSTALL_DIR = /usr/local

all: tippecanoe_install


$(TIPPECANOE_TARBALL):
	wget https://github.com/felt/tippecanoe/archive/refs/tags/$(TIPPECANOE_VERSION).tar.gz -O $(TIPPECANOE_TARBALL)

$(TIPPECANOE_SRC_DIR): $(TIPPECANOE_TARBALL)
	tar -xvzf $(TIPPECANOE_TARBALL)

build_tippecanoe: $(TIPPECANOE_SRC_DIR)
	cd $(TIPPECANOE_SRC_DIR) && make && sudo make install PREFIX=$(INSTALL_DIR)

tippecanoe_install:
	@if command -v $(INSTALL_DIR)/bin/tippecanoe >/dev/null 2>&1; then \
		echo "tippecanoe already installed, skipping build."; \
	else \
		$(MAKE) build_tippecanoe; \
	fi

clean:
	rm -rf $(TIPPECANOE_SRC_DIR) $(TIPPECANOE_TARBALL)