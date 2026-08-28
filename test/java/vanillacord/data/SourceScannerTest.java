package vanillacord.data;

import org.junit.jupiter.api.Test;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.ClassWriter;
import org.objectweb.asm.MethodVisitor;
import org.objectweb.asm.Opcodes;
import vanillacord.packaging.Package;

import java.nio.file.Path;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

class SourceScannerTest {

    private static final class StubPackage extends Package {
        @Override
        public ZipInputStream read(Path path) {
            throw new UnsupportedOperationException("stub");
        }

        @Override
        public ZipOutputStream write(Path path) {
            throw new UnsupportedOperationException("stub");
        }
    }

    @Test
    void identifiesHookPointsFromLiterals() {
        StubPackage file = new StubPackage();
        byte[] bytes = buildProbeClass();

        scan(file, bytes);

        assertNotNull(file.sources.startup, "startup not detected");
        assertNotNull(file.sources.login, "login not detected");
        assertNotNull(file.sources.handshake, "handshake not detected");
        assertNotNull(file.sources.send, "send not detected");
        assertNotNull(file.sources.receive, "receive not detected");
    }

    @Test
    void ignoresLoginAcknowledgementDiagnostic() {
        StubPackage file = new StubPackage();
        ClassWriter cw = probeClass();
        addStringLdcMethod(cw, "acknowledgement", "Unexpected login acknowledgement packet");
        addStringLdcMethod(cw, "hello", "Unexpected hello packet");
        cw.visitEnd();

        scan(file, cw.toByteArray());

        assertNotNull(file.sources.login);
        assertEquals("hello", file.sources.login.name);
    }

    @Test
    void strongHelloSignalReplacesWeakFallback() {
        StubPackage file = new StubPackage();
        ClassWriter cw = probeClass();
        addStringLdcMethod(cw, "weak", "Unexpected login packet");
        addStringLdcMethod(cw, "strong", "Unexpected hello packet");
        cw.visitEnd();

        scan(file, cw.toByteArray());

        assertEquals("strong", file.sources.login.name);
    }

    @Test
    void weakFallbackCannotOverwriteStrongHelloSignal() {
        StubPackage file = new StubPackage();
        ClassWriter cw = probeClass();
        addStringLdcMethod(cw, "strong", "Received hello twice");
        addStringLdcMethod(cw, "weak", "Unexpected login packet");
        cw.visitEnd();

        scan(file, cw.toByteArray());

        assertEquals("strong", file.sources.login.name);
    }

    @Test
    void rejectsAmbiguousStrongLoginMethods() {
        StubPackage file = new StubPackage();
        ClassWriter cw = probeClass();
        addStringLdcMethod(cw, "firstHello", "Unexpected hello packet");
        addStringLdcMethod(cw, "secondHello", "Received hello twice");
        cw.visitEnd();

        IllegalStateException error = assertThrows(IllegalStateException.class,
                () -> scan(file, cw.toByteArray()));
        assertEquals("Ambiguous login hook candidates: firstHello()V and secondHello()V", error.getMessage());
    }

    @Test
    void rejectsAmbiguousWeakLoginMethods() {
        StubPackage file = new StubPackage();
        ClassWriter cw = probeClass();
        addStringLdcMethod(cw, "firstFallback", "Unexpected login packet");
        addStringLdcMethod(cw, "secondFallback", "Unexpected login request");
        cw.visitEnd();

        IllegalStateException error = assertThrows(IllegalStateException.class,
                () -> scan(file, cw.toByteArray()));
        assertEquals("Ambiguous login hook candidates: firstFallback()V and secondFallback()V", error.getMessage());
    }

    @Test
    void allowsMultipleStrongSignalsInSameLoginMethod() {
        StubPackage file = new StubPackage();
        ClassWriter cw = probeClass();
        MethodVisitor mv = cw.visitMethod(Opcodes.ACC_PUBLIC, "hello", "()V", null, null);
        mv.visitCode();
        mv.visitLdcInsn("Unexpected hello packet");
        mv.visitInsn(Opcodes.POP);
        mv.visitLdcInsn("Received hello twice");
        mv.visitInsn(Opcodes.POP);
        mv.visitInsn(Opcodes.RETURN);
        mv.visitMaxs(1, 1);
        mv.visitEnd();
        cw.visitEnd();

        scan(file, cw.toByteArray());

        assertEquals("hello", file.sources.login.name);
    }

    private static void scan(StubPackage file, byte[] bytes) {
        new ClassReader(bytes).accept(new SourceScanner(file), ClassReader.SKIP_FRAMES | ClassReader.SKIP_DEBUG);
    }

    private static byte[] buildProbeClass() {
        ClassWriter cw = probeClass();

        addStringLdcMethod(cw, "startup", "Server console handler");
        addStringLdcMethod(cw, "login", "Unexpected hello");
        addStringLdcMethod(cw, "handshake", "outdated client! please use");
        addStringLdcMethod(cw, "send", "payload too large");
        addStringLdcMethod(cw, "receive", "payload too large");

        cw.visitEnd();
        return cw.toByteArray();
    }

    private static ClassWriter probeClass() {
        ClassWriter cw = new ClassWriter(0);
        cw.visit(Opcodes.V21, Opcodes.ACC_PUBLIC, "vanillacord/test/Probe", null, "java/lang/Object", null);
        // Non-static int field enables the login extension detection path.
        cw.visitField(Opcodes.ACC_PUBLIC, "tid", "I", null, null).visitEnd();
        return cw;
    }

    private static void addStringLdcMethod(ClassWriter cw, String name, String literal) {
        MethodVisitor mv = cw.visitMethod(Opcodes.ACC_PUBLIC, name, "()V", null, null);
        mv.visitCode();
        mv.visitLdcInsn(literal);
        mv.visitInsn(Opcodes.POP);
        mv.visitInsn(Opcodes.RETURN);
        mv.visitMaxs(1, 1);
        mv.visitEnd();
    }
}
