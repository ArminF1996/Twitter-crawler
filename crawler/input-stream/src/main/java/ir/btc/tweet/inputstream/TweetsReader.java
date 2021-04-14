package ir.btc.tweet.inputstream;

import org.apache.commons.codec.Charsets;
import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.auth.AuthenticationException;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.methods.HttpRequestBase;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.auth.BasicScheme;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.Closeable;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UncheckedIOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;

public class TweetsReader implements Closeable {

    private static final Logger logger = LoggerFactory.getLogger(TweetsReader.class);
    private Configs configs;
    private BitweetFile tweetsFile;
    private volatile boolean isRunning;
    private String token;
    private int connectionTimeout;

    public TweetsReader(Configs configs) throws IOException, AuthenticationException {
        this.isRunning = false;
        this.configs = configs;
        tweetsFile = new BitweetFile(configs.getTweetsMaxFileSizeMb(), configs.getTweetsDirectoryName(),
                configs.getTweetsFileNameExtension(), configs.getTweetsFileNamePattern());
        getBearerToken();
    }

    private JSONObject requestToJsonResponse(HttpRequestBase request, int responseCode) throws IOException {

        try (CloseableHttpClient client = HttpClients.createDefault()) {
            CloseableHttpResponse response = client.execute(request);
            HttpEntity entity = response.getEntity();
            Header encodingHeader = entity.getContentEncoding();
            Charset encoding = encodingHeader == null ? StandardCharsets.UTF_8 :
                    Charsets.toCharset(encodingHeader.getValue());
            JSONObject res = new JSONObject(EntityUtils.toString(entity, encoding));
            if (response.getStatusLine().getStatusCode() != responseCode) {
                throw new AssertionError("This request does not work, response status code is:\t"
                        + response.getStatusLine().getStatusCode() + "\n response is:\t" + res);
            }
            return res;
        }
    }

    private void getBearerToken() throws IOException, AuthenticationException {

        if (token != null) {
            return;
        }
        HttpPost httpPost = new HttpPost(configs.getApiBearerTokenUrl());
        httpPost.setEntity(new StringEntity("grant_type=client_credentials"));
        httpPost.addHeader("User-Agent", "My Twitter app!");
        httpPost.addHeader("Content-Type", "application/x-www-form-urlencoded");
        UsernamePasswordCredentials creds
                = new UsernamePasswordCredentials(configs.getApiConsumerKey(), configs.getApiConsumerSecret());
        httpPost.addHeader(new BasicScheme().authenticate(creds, httpPost, null));
        JSONObject json = requestToJsonResponse(httpPost, 200);
        token = json.getString("access_token");
        logger.info("Bearer token successfully received.");
    }

    public JSONObject getAllRules() throws IOException {
        HttpGet httpGet = new HttpGet(configs.getApiRulesUrl());
        httpGet.addHeader("Authorization", "bearer ".concat(token));
        JSONObject rules = requestToJsonResponse(httpGet, 200);
        logger.info("Rules successfully received \n{}", rules);
        return rules;
    }

    public void deleteRules(JSONObject rules) throws IOException {

        if (rules == JSONObject.NULL || !rules.has("data")) {
            logger.warn("Json rules is empty, so no rules be deleted.");
            return;
        }
        HttpPost httpPost = new HttpPost(configs.getApiRulesUrl());
        httpPost.addHeader("Authorization", "bearer ".concat(token));
        httpPost.addHeader("Content-Type", "application/json");

        ArrayList<String> ids = new ArrayList<>();
        rules.getJSONArray("data").forEach(obj -> {
            ids.add(((JSONObject) obj).getString("id"));
        });
        JSONObject payload = new JSONObject().put("delete", new JSONObject().put("ids", new JSONArray(ids)));
        httpPost.setEntity(new StringEntity(payload.toString()));
        JSONObject json = requestToJsonResponse(httpPost, 200).getJSONObject("meta").getJSONObject("summary");
        logger.info("deleted rules: {}\nnot_deleted rules: {}", json.get("deleted"), json.get("not_deleted"));
    }

    public void resetRules() throws IOException {
        deleteRules(getAllRules());
        addRules(configs.getTweetsRulesFilePath());
        logger.info("rules successfully be reset.");
    }

    public void addRules(String rulesFilePath) throws IOException {
        File jsonFile = new File(rulesFilePath);
        if (!jsonFile.exists()) {
            logger.warn("Json rule files does not exists.");
        }
        String payload = new String(Files.readAllBytes(Paths.get(rulesFilePath)));
        HttpPost httpPost = new HttpPost(configs.getApiRulesUrl());
        httpPost.addHeader("Authorization", "bearer ".concat(token));
        httpPost.addHeader("Content-Type", "application/json");
        httpPost.setEntity(new StringEntity(payload));
        requestToJsonResponse(httpPost, 201);
        logger.info("rules successfully added.");
    }

    public void start() {
        isRunning = true;
        logger.info("TweetsReader successfully started!");
        connectionTimeout = 5;
        while (isRunning) {
            try {
                readStream();
            } catch (IOException e) {
                logger.error("IOException received in stream reader!", e);
            } catch (UncheckedIOException e) {
                logger.error("UncheckedIOException received in stream reader!", e);
            }
            try {
                TimeUnit.SECONDS.sleep(connectionTimeout);
            } catch (InterruptedException e) {
                if (isRunning) {
                    throw new AssertionError("Unexpected interrupt exception", e);
                }
            }
            connectionTimeout = Integer.min(connectionTimeout * 2, 15 * 60);
        }
    }

    private void readStream() throws IOException, UncheckedIOException {

        CloseableHttpClient httpclient = HttpClients.createDefault();
        HttpGet httpget = new HttpGet(configs.getApiStreamUrl());
        httpget.addHeader("Authorization", "bearer ".concat(token));
        CloseableHttpResponse response = httpclient.execute(httpget);
        try {
            HttpEntity entity = response.getEntity();
            if (entity != null) {
                try (BufferedReader streamReader = new BufferedReader(new InputStreamReader(entity.getContent()))) {
                    streamReader.lines().forEach(line -> {
                        try {
                            tweetsFile.writeln(line);
                        } catch (IOException e) {
                            logger.error("Can not write on tweetsFile!", e);
                        }
                    });
                }
            }
        } finally {
            response.close();
            httpclient.close();
        }
    }

    public void close() {
        isRunning = false;
        tweetsFile.close();
        logger.info("TweetsReader successfully stopped!");
    }

    public static void main(String[] args) throws IOException, AuthenticationException {
        if (args.length != 1) {
            System.err.println("please enter just the configs path as input args!");
            System.exit(1);
        }
        Configs configs = new Configs(args[0]);
        TweetsReader tweetsReader = new TweetsReader(configs);
        tweetsReader.resetRules();
        tweetsReader.start();
        Runtime.getRuntime().addShutdownHook(new Thread(tweetsReader::close));
    }
}
