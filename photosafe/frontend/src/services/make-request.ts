const makeRequest = async <T extends unknown>(
  input: RequestInfo,
  init?: RequestInit,
): Promise<T> => {
  const response = await fetch(input, init)

  if (!response.ok) {
    throw RequestError.forStatus(response.status)
  }

  const textResponse = await response.text()
  return textResponse ? JSON.parse(textResponse) : {}
}

export default makeRequest

export class RequestError extends Error {
  status: number
  message: string

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.message = message
  }

  static forStatus(status: number) {
    const message = ((httpStatus: number) => {
      switch (httpStatus) {
        case 400:
          return "bad request"
        case 401:
          return "unauthorized"
        case 403:
          return "forbidden"
        case 404:
          return "not found"
        case 409:
          return "conflict"
        case 500:
          return "something went wrong"
        default:
          return "something went wrong"
      }
    })(status)

    return new RequestError(status, message)
  }
}
