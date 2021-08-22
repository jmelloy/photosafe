const makeRequest = async <T extends unknown>(
  input: RequestInfo,
  init?: RequestInit
): Promise<T> => {
  const response = await fetch(input, init);
  console.log(response);
  if (!response.ok) {
    throw new RequestError(response);
  }

  const textResponse = await response.text();
  return textResponse ? JSON.parse(textResponse) : {};
};

export default makeRequest;

export class RequestError extends Error {
  status: number;
  message: string;

  constructor(response: Response) {
    super(response.statusText);
    this.status = response.status;
    this.message = response.statusText;
  }
}
