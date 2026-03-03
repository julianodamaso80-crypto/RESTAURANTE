import useSWR from "swr";
import api from "@/lib/api";
import type { KDSTicket, KDSStation } from "@/types/api";

interface PaginatedResult<T> {
  results: T[];
}

const fetcher = (url: string) => api.get(url).then((r) => r.data);

export function useKDSStations() {
  const { data, error } = useSWR<PaginatedResult<KDSStation>>(
    "/kds/stations/",
    fetcher,
    { refreshInterval: 30000 },
  );
  return {
    stations: data?.results ?? [],
    loading: !data && !error,
    error,
  };
}

export function useKDSTickets(stationId?: string) {
  const url = stationId
    ? `/kds/stations/${stationId}/tickets/?status=WAITING,IN_PROGRESS`
    : `/kds/tickets/?status=WAITING,IN_PROGRESS`;

  const { data, error, mutate } = useSWR<PaginatedResult<KDSTicket>>(
    url,
    fetcher,
    { refreshInterval: 5000 },
  );

  return {
    tickets: data?.results ?? [],
    loading: !data && !error,
    error,
    refresh: mutate,
  };
}

export async function advanceTicketStatus(
  ticketId: string,
  newStatus: "IN_PROGRESS" | "DONE",
) {
  await api.patch(`/kds/tickets/${ticketId}/`, { status: newStatus });
}
