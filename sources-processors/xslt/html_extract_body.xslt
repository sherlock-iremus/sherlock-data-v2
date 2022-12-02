<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet expand-text="yes" version="3.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xpath-default-namespace="http://www.w3.org/1999/xhtml">
    <xsl:output encoding="UTF-8" indent="yes" method="xml" omit-xml-declaration="yes"/>
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="body">
        <xsl:apply-templates/>
    </xsl:template>
</xsl:stylesheet>
