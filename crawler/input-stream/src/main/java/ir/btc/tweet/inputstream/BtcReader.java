package ir.btc.tweet.inputstream;

import org.apache.commons.codec.Charsets;
import org.apache.http.Header;
import org.apache.http.HttpEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Closeable;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.concurrent.TimeUnit;

public class BtcReader implements Closeable {

    private static final Logger logger = LoggerFactory.getLogger(BtcReader.class);
    private Configs configs;
    private BitweetFile btcFile;
    private volatile boolean isRunning;

    public BtcReader(Configs configs) {
        this.configs = configs;
        btcFile = new BitweetFile(configs.getBtcMaxFileSizeMb(), configs.getBtcDirectoryName(),
                configs.getBtcFileNameExtension(), configs.getBtcFileNamePattern());
    }

    public void start() {
        isRunning = true;
        logger.info("BtcReader successfully started!");
        while (isRunning) {
            try {
                updateBtcPrice();
            } catch (IOException ignored) {
                continue;
            }
            try {
                TimeUnit.MINUTES.sleep(5);
            } catch (InterruptedException e) {
                if (isRunning) {
                    e.printStackTrace();
                }
            }
        }
    }

    private void updateBtcPrice() throws IOException {

        CloseableHttpClient client = HttpClients.createDefault();
        HttpGet httpGet = new HttpGet(configs.getBtcApiPriceUrl());
        CloseableHttpResponse response = client.execute(httpGet);
        if (!response.getStatusLine().getReasonPhrase().equals("OK")) {
            logger.error("Can not get the latest btc price, response code is: {}",
                    response.getStatusLine().getStatusCode());
            client.close();
            return;
        }
        HttpEntity entity = response.getEntity();
        Header encodingHeader = entity.getContentEncoding();
        Charset encoding = encodingHeader == null ? StandardCharsets.UTF_8 :
                Charsets.toCharset(encodingHeader.getValue());
        JSONObject res = new JSONObject(EntityUtils.toString(entity, encoding));
        res.put("time", Instant.now());
        btcFile.writeln(res.toString());
        client.close();
        logger.info("Btc price successfully updated.");
    }

    public void close() {
        isRunning = false;
        btcFile.close();
        logger.info("BtcReader successfully stopped!");
    }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) {
            System.err.println("please enter just the configs path as input args!");
            System.exit(1);
        }
        Configs configs = new Configs(args[0]);
        BtcReader btcReader = new BtcReader(configs);
        btcReader.start();
        Runtime.getRuntime().addShutdownHook(new Thread(btcReader::close));
    }
}
