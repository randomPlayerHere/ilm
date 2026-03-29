import { onQueueJobComplete, emitQueueJobComplete } from "../queue-events";

// queue-events is a module-level singleton — listeners persist between tests unless cleaned up.
// Each test registers and unregisters its own listeners to keep tests isolated.

describe("queue-events", () => {
  it("calls a registered listener when an event is emitted", () => {
    const listener = jest.fn();
    const unsubscribe = onQueueJobComplete(listener);

    emitQueueJobComplete("asgn_1", "job_1");

    expect(listener).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledWith("asgn_1", "job_1");

    unsubscribe();
  });

  it("does not call the listener after unsubscribe", () => {
    const listener = jest.fn();
    const unsubscribe = onQueueJobComplete(listener);
    unsubscribe();

    emitQueueJobComplete("asgn_1", "job_1");

    expect(listener).not.toHaveBeenCalled();
  });

  it("calls all registered listeners on emit", () => {
    const listener1 = jest.fn();
    const listener2 = jest.fn();
    const unsub1 = onQueueJobComplete(listener1);
    const unsub2 = onQueueJobComplete(listener2);

    emitQueueJobComplete("asgn_2", "job_2");

    expect(listener1).toHaveBeenCalledWith("asgn_2", "job_2");
    expect(listener2).toHaveBeenCalledWith("asgn_2", "job_2");

    unsub1();
    unsub2();
  });

  it("does not call an unsubscribed listener while other listeners remain active", () => {
    const listener1 = jest.fn();
    const listener2 = jest.fn();
    const unsub1 = onQueueJobComplete(listener1);
    const unsub2 = onQueueJobComplete(listener2);

    unsub1();
    emitQueueJobComplete("asgn_3", "job_3");

    expect(listener1).not.toHaveBeenCalled();
    expect(listener2).toHaveBeenCalledWith("asgn_3", "job_3");

    unsub2();
  });
});
