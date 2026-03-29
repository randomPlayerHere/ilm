import { useEffect, useState } from "react";
import NetInfo from "@react-native-community/netinfo";

export interface NetworkStatus {
  isConnected: boolean | null;
}

export function useNetworkStatus(): NetworkStatus {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsConnected(state.isConnected);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  return { isConnected };
}
