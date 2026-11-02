# Default target
all: binaries

GO_WAGGLE_REPO ?= https://github.com/sukunrt/go-waggle.git
GO_WAGGLE_REV ?= 133ad8e2061d3e442d985346e795cee40f6c78f5
GO_WAGGLE_DIR := go-libp2p/go-waggle

NIM_LIBP2P_REPO ?= https://github.com/iftech/nim-libp2p.git
NIM_LIBP2P_REV ?= 27eeb5b17d8618b32c743f151eac759df990d0d5
NIM_LIBP2P_DIR := nim-libp2p/nim-libp2p

binaries:
	cd rust-libp2p && cargo build
	test -d $(GO_WAGGLE_DIR) || git clone -q $(GO_WAGGLE_REPO) $(GO_WAGGLE_DIR)
	git -C $(GO_WAGGLE_DIR) fetch -q origin
	git -C $(GO_WAGGLE_DIR) checkout -q --detach $(GO_WAGGLE_REV)
	cd $(GO_WAGGLE_DIR)/interop && go build -o $(CURDIR)/go-libp2p/waggle-bin .

	test -d $(NIM_LIBP2P_DIR) || git clone -q --filter=blob:none --no-checkout $(NIM_LIBP2P_REPO) $(NIM_LIBP2P_DIR)
	git -C $(NIM_LIBP2P_DIR) fetch -q --depth 1 origin $(NIM_LIBP2P_REV)
	git -C $(NIM_LIBP2P_DIR) checkout -q --detach FETCH_HEAD
	cd $(NIM_LIBP2P_DIR) && nimble --noLockfile --requires:"nim == 2.2.10" --resolver:minver -l setup -y
	cd $(NIM_LIBP2P_DIR) && nim c --threads:on -d:chronicles_log_level=WARN \
		-d:chronicles_default_output_device=stderr \
		--warningAsError:UseBase:off --warningAsError:UnusedImport:off \
		--warningAsError:Deprecated:off --hintAsError:XCannotRaiseY:off \
		--out:$(CURDIR)/nim-libp2p/waggle-bin interop/waggle/test-plans/peer.nim

# Clean all generated shadow simulation files
clean:
	rm -rf shadow-outputs || true
	rm plots/* || true

test:
	# Testing waggle dissemination
	@echo "Testing waggle"
	@uv run run.py --node_count 8 --composition rust --scenario "waggle" && uv run checks/dissemination.py latest --count 1

.PHONY: binaries all clean test
