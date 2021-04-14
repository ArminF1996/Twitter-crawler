package ir.btc.tweet.inputstream;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedOutputStream;
import java.io.Closeable;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;


public class BitweetFile implements Closeable {

    private static final Logger logger = LoggerFactory.getLogger(BitweetFile.class);
    private File file;
    private String fileExtension;
    private BufferedOutputStream writer;
    private String directoryName;
    private int maxFileSize;
    private DateTimeFormatter fileDateTimeFormatter;

    public BitweetFile(int maxFileSize, String directoryName, String fileExtension, String formatter) {
        this.maxFileSize = maxFileSize;
        this.directoryName = directoryName;
        this.fileExtension = fileExtension;
        this.fileDateTimeFormatter = DateTimeFormatter.ofPattern(formatter, Locale.getDefault())
                .withZone(ZoneId.of("UTC"));
        new File(directoryName).mkdirs();
    }

    private void createNewFile() throws FileNotFoundException {
        String fileName = fileDateTimeFormatter.format(Instant.now());
        file = new File(directoryName, fileName.concat(fileExtension));
        if (writer != null) {
            close();
        }
        writer = new BufferedOutputStream(new FileOutputStream(file));
    }

    private void checkFile() throws FileNotFoundException {
        if (file == null || !file.exists() || this.getSize() >= maxFileSize) {
            createNewFile();
        }
    }

    public void writeln(String content) throws IOException {
        checkFile();
        writer.write(content.getBytes());
        writer.write("\n".getBytes());
        writer.flush();
    }

    public void write(String content) throws IOException {
        checkFile();
        writer.write(content.getBytes());
    }

    public void close() {
        if (writer == null)
            return;
        try {
            writer.flush();
            writer.close();
        } catch (IOException e) {
            logger.warn("Can not close the writer for {} files.", fileExtension, e);
        }
    }

    private long getSize() {
        long size = file.length();
        size /= (1024 * 1024);
        return size;
    }
}
