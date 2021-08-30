import React, { FunctionComponent } from "react";
import { Route, Redirect, RouteProps } from "react-router-dom";
import { useAuth } from "../services/auth-service";

const ProtectedRoute: FunctionComponent<RouteProps> = ({
  children,
  ...rest
}) => {
  const auth = useAuth();
  const isAuthenticated = !!auth.isAuthenticated();

  // console.log(auth.isAuthenticated(), isAuthenticated, auth.getToken());
  return (
    <Route {...rest}>
      {isAuthenticated ? (
        children
      ) : (
        <Redirect
          to={{
            pathname: "/login",
            state: { redirectPath: rest.location?.pathname },
          }}
        />
      )}
    </Route>
  );
};

export default ProtectedRoute;
