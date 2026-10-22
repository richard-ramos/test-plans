# Default target
all: binaries

GO_WAGGLE_REPO ?= https://github.com/sukunrt/go-waggle.git
GO_WAGGLE_REV ?= 133ad8e2061d3e442d985346e795cee40f6c78f5
GO_WAGGLE_DIR := go-libp2p/go-waggle

binaries:
	cd rust-libp2p && cargo build
	test -d $(GO_WAGGLE_DIR) || git clone -q $(GO_WAGGLE_REPO) $(GO_WAGGLE_DIR)
	git -C $(GO_WAGGLE_DIR) fetch -q origin
	git -C $(GO_WAGGLE_DIR) checkout -q --detach $(GO_WAGGLE_REV)
	cd $(GO_WAGGLE_DIR)/interop && go build -o $(CURDIR)/go-libp2p/waggle-bin .

# Clean all generated shadow simulation files
clean:
	rm -rf shadow-outputs || true
	rm plots/* || true

test:
	# Testing waggle dissemination
	@echo "Testing waggle"
	@uv run run.py --node_count 8 --composition rust --scenario "waggle" && uv run checks/dissemination.py latest --count 1

.PHONY: binaries all clean test
