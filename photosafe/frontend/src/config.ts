/* eslint-disable no-template-curly-in-string */
interface AppConfig {
  baseUrl: string | undefined;
  environmentName: string;
}

const localConfig: AppConfig = {
  environmentName: "local",
  baseUrl: process.env.REACT_APP_SERVER_ADDRESS,
};

const config: AppConfig = localConfig;

export default config;
