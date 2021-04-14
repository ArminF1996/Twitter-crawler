package ir.btc.tweet.inputstream;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.Properties;

public class Configs {

    private final static String TWEETS_MAX_FILE_SIZE_MB = "tweets.max.file.size.mb";
    private final static String TWEETS_DIRECTORY_NAME = "tweets.directory.name";
    private final static String TWEETS_FILE_NAME_PATTERN = "tweets.file.name.pattern";
    private final static String TWEETS_FILE_NAME_EXTENSION = "tweets.file.name.extension";
    private final static String TWEETS_RULES_FILE_PATH = "tweets.rules.file.path";
    private final static String TWITTER_API_CONSUMER_KEY = "twitter.api.consumer.key";
    private final static String TWITTER_API_CONSUMER_SECRET = "twitter.api.consumer.secret";
    private final static String TWITTER_API_STREAM_URL = "twitter.api.stream.url";
    private final static String TWITTER_API_RULES_URL = "twitter.api.rules.url";
    private final static String TWITTER_API_BEARER_TOKEN_URL = "twitter.api.bearer.token.url";
    private final static String BTC_MAX_FILE_SIZE_MB = "btc.max.file.size.mb";
    private final static String BTC_DIRECTORY_NAME = "btc.directory.name";
    private final static String BTC_FILE_NAME_PATTERN = "btc.file.name.pattern";
    private final static String BTC_FILE_NAME_EXTENSION = "btc.file.name.extension";
    private final static String BTC_API_PRICE_URL = "btc.api.price.url";

    private Properties properties;

    public Configs(String configsPath) throws IOException {
        properties = new Properties();
        properties.load(new FileInputStream(configsPath));
    }

    public int getTweetsMaxFileSizeMb() {
        return Integer.parseInt(properties.getProperty(TWEETS_MAX_FILE_SIZE_MB));
    }

    public String getTweetsDirectoryName() {
        return properties.getProperty(TWEETS_DIRECTORY_NAME);
    }

    public String getTweetsFileNamePattern() {
        return properties.getProperty(TWEETS_FILE_NAME_PATTERN);
    }

    public String getTweetsFileNameExtension() {
        return properties.getProperty(TWEETS_FILE_NAME_EXTENSION);
    }

    public String getTweetsRulesFilePath() {
        return properties.getProperty(TWEETS_RULES_FILE_PATH);
    }

    public String getApiConsumerKey() {
        return properties.getProperty(TWITTER_API_CONSUMER_KEY);
    }

    public String getApiConsumerSecret() {
        return properties.getProperty(TWITTER_API_CONSUMER_SECRET);
    }

    public String getApiStreamUrl() {
        return properties.getProperty(TWITTER_API_STREAM_URL);
    }

    public String getApiRulesUrl() {
        return properties.getProperty(TWITTER_API_RULES_URL);
    }

    public String getApiBearerTokenUrl() {
        return properties.getProperty(TWITTER_API_BEARER_TOKEN_URL);
    }

    public int getBtcMaxFileSizeMb() {
        return Integer.parseInt(properties.getProperty(BTC_MAX_FILE_SIZE_MB));
    }

    public String getBtcDirectoryName() {
        return properties.getProperty(BTC_DIRECTORY_NAME);
    }

    public String getBtcFileNamePattern() {
        return properties.getProperty(BTC_FILE_NAME_PATTERN);
    }

    public String getBtcFileNameExtension() {
        return properties.getProperty(BTC_FILE_NAME_EXTENSION);
    }

    public String getBtcApiPriceUrl() {
        return properties.getProperty(BTC_API_PRICE_URL);
    }
}
