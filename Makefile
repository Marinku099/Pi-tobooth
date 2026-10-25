all clean install:
	$(MAKE) -C src/storage $@
	$(MAKE) -C src/camera $@

.PHONY: all clean install
