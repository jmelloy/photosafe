import React, { FunctionComponent } from "react"
import "./LoadingSpinner.css"

const LoadingSpinner: FunctionComponent = () => {
  return (
    <div className="lds-ring">
      <div></div>
      <div></div>
      <div></div>
      <div></div>
    </div>
  )
}

export default LoadingSpinner
