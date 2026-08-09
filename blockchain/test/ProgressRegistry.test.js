const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ProgressRegistry", function () {
  let registry, owner, backend, stranger;

  beforeEach(async function () {
    [owner, backend, stranger] = await ethers.getSigners();

    const ProgressRegistry = await ethers.getContractFactory("ProgressRegistry");
    registry = await ProgressRegistry.deploy();
    await registry.waitForDeployment();
  });

  it("makes the deployer both owner and an approved writer", async function () {
    expect(await registry.owner()).to.equal(owner.address);
    expect(await registry.writers(owner.address)).to.equal(true);
  });

  it("lets the owner approve a new writer", async function () {
    await registry.setWriter(backend.address, true);
    expect(await registry.writers(backend.address)).to.equal(true);
  });

  it("blocks non-writers from anchoring records", async function () {
    const hash = ethers.keccak256(ethers.toUtf8Bytes("evidence-photo-1"));

    await expect(
      registry.connect(stranger).addRecord(1, 1, 0, hash)
    ).to.be.revertedWith("ProgressRegistry: caller is not an approved writer");
  });

  it("anchors a record and makes it retrievable", async function () {
    await registry.setWriter(backend.address, true);

    const hash = ethers.keccak256(ethers.toUtf8Bytes("evidence-photo-1"));
    const tx = await registry.connect(backend).addRecord(1, 42, 0, hash);
    await tx.wait();

    expect(await registry.recordCount()).to.equal(1);
    expect(await registry.isHashAnchored(hash)).to.equal(true);

    const record = await registry.getRecord(0);
    expect(record.projectId).to.equal(1);
    expect(record.referenceId).to.equal(42);
    expect(record.dataHash).to.equal(hash);
    expect(record.submittedBy).to.equal(backend.address);

    const indexes = await registry.getProjectRecordIndexes(1);
    expect(indexes.length).to.equal(1);
    expect(indexes[0]).to.equal(0);
  });

  it("rejects a zero hash", async function () {
    await expect(
      registry.addRecord(1, 1, 0, ethers.ZeroHash)
    ).to.be.revertedWith("ProgressRegistry: empty hash");
  });
});
