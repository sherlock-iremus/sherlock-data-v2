<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0" 
    xpath-default-namespace="http://www.tei-c.org/ns/1.0">
    <!-- DÉCOUPER EN ARTICLES -->
    <xsl:template match="//div[@type='article']">
        <xsl:result-document method="xml" href="{@xml:id}.xml">
            <xsl:copy-of select="." />
        </xsl:result-document>
    </xsl:template>
</xsl:stylesheet>