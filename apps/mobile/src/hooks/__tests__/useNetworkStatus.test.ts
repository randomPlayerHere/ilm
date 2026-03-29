import type { NetInfoState, NetInfoSubscription } from "@react-native-community/netinfo";

let capturedListener: ((state: NetInfoState) => void) | null = null;
const mockUnsubscribe = jest.fn();

jest.mock("@react-native-community/netinfo", () => ({
  __esModule: true,
  default: {
    addEventListener: jest.fn((listener: (state: NetInfoState) => void) => {
      capturedListener = listener;
      return mockUnsubscribe;
    }),
  },
}));

import { renderHook, act } from "@testing-library/react-native";
import { useNetworkStatus } from "../useNetworkStatus";

function makeNetInfoState(isConnected: boolean | null): NetInfoState {
  return {
    isConnected,
    isInternetReachable: isConnected,
    type: "wifi",
    isWifiEnabled: true,
    details: null,
  } as unknown as NetInfoState;
}

beforeEach(() => {
  jest.clearAllMocks();
  capturedListener = null;
});

describe("useNetworkStatus", () => {
  it("returns isConnected=null before NetInfo fires an event", () => {
    const { result } = renderHook(() => useNetworkStatus());
    expect(result.current.isConnected).toBeNull();
  });

  it("returns isConnected=true when NetInfo reports connected", () => {
    const { result } = renderHook(() => useNetworkStatus());
    act(() => {
      capturedListener?.(makeNetInfoState(true));
    });
    expect(result.current.isConnected).toBe(true);
  });

  it("returns isConnected=false when NetInfo reports disconnected", () => {
    const { result } = renderHook(() => useNetworkStatus());
    act(() => {
      capturedListener?.(makeNetInfoState(false));
    });
    expect(result.current.isConnected).toBe(false);
  });

  it("updates isConnected when connectivity changes", () => {
    const { result } = renderHook(() => useNetworkStatus());
    act(() => { capturedListener?.(makeNetInfoState(true)); });
    expect(result.current.isConnected).toBe(true);
    act(() => { capturedListener?.(makeNetInfoState(false)); });
    expect(result.current.isConnected).toBe(false);
  });

  it("calls addEventListener on mount", () => {
    const NetInfo = require("@react-native-community/netinfo").default;
    renderHook(() => useNetworkStatus());
    expect(NetInfo.addEventListener).toHaveBeenCalledTimes(1);
  });

  it("unsubscribes listener on unmount", () => {
    const { unmount } = renderHook(() => useNetworkStatus());
    unmount();
    expect(mockUnsubscribe).toHaveBeenCalledTimes(1);
  });
});
